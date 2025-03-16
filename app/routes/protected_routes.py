import logging
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import FastAPI, Request
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.exception import AuthenticationError, CustomException
from app.extensions import get_db, SessionLocal
from app.models import models
from app.models.otp import OTP
from app.models.user import User
from app.utils.security_utils import verify_access_token

router = APIRouter(tags=["Monitoring & Protected"])
logger = logging.getLogger(__name__)

START_TIME = time.time()
REQUEST_COUNT = 0
ERROR_COUNT = 0
RESPONSE_TIMES = []


def get_uptime():
    """Calculates and returns application uptime in human-readable format."""
    uptime_seconds = int(time.time() - START_TIME)
    minutes, seconds = divmod(uptime_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


async def check_database_health(db: Session):
    """Checks the health of the database connection."""
    try:
        # db.execute(text("SELECT 1"))  # Simple SQLAlchemy 2.0 style execution
        # db_connection_stats = engine.pool.status()  # Get connection pool stats
        engine = db.bind  # The engine bound to the session
        connection_details = {key: str(value) for key, value in engine.pool.__dict__.items()}
        # Get additional database connection details like name, version, server info
        with engine.connect() as connection:
            db_info = {}

            # Get database name and version based on the database system (PostgreSQL, MySQL, SQL Server)
            db_type = connection.dialect.name  # 'postgresql', 'mysql', 'mssql', etc.

            if db_type == 'postgresql':
                # PostgreSQL specific queries
                db_name = connection.execute(text("SELECT current_database()")).scalar()
                db_version = connection.execute(text("SELECT version()")).scalar()
                db_size = connection.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
                uptime = connection.execute(text("SELECT now() - pg_postmaster_start_time()")).scalar()

                # Get user details
                users = connection.execute(text("SELECT usename FROM pg_user")).fetchall()

                # Get schemas for each user
                schemas = connection.execute(text("SELECT schema_name FROM information_schema.schemata")).fetchall()

                # Get tables, columns, row counts, and their sizes for each schema
                tables_info = {}
                for schema in schemas:
                    schema_name = schema[0]
                    tables = connection.execute(text(f"""
                        SELECT table_name,
                               COUNT(*) AS column_count,
                               (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = '{schema_name}' AND table_name = t.table_name) AS column_count,
                               pg_size_pretty(pg_total_relation_size(quote_ident('{schema_name}') || '.' || quote_ident(t.table_name))) AS table_size
                        FROM information_schema.tables t
                        WHERE table_schema = '{schema_name}'
                        GROUP BY t.table_name
                    """)).fetchall()

                    tables_info[schema_name] = {
                        table[0]: {
                            "column_count": table[1],
                            "table_size": table[2]
                        } for table in tables
                    }

                # Add information to db_info
                db_info.update({
                    "db_name": db_name,
                    "db_version": db_version,
                    "db_size": db_size,
                    "uptime": str(uptime),
                    "users": [user[0] for user in users],
                    "schemas": [schema[0] for schema in schemas],
                    "tables_info": tables_info,
                    "server": connection.execute(text("SELECT inet_server_addr()")).scalar(),
                    "port": connection.execute(text("SELECT inet_server_port()")).scalar()
                })

            elif db_type == 'mysql':
                # MySQL specific queries
                db_name = connection.execute(text("SELECT DATABASE()")).scalar()
                db_version = connection.execute(text("SELECT VERSION()")).scalar()
                db_size = connection.execute(text("SELECT table_schema AS 'database', "
                                                  "ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_in_mb' "
                                                  "FROM information_schema.tables WHERE table_schema = DATABASE() "
                                                  "GROUP BY table_schema")).scalar()
                uptime = connection.execute(text("SHOW STATUS LIKE 'Uptime'")).fetchone()[1]

                # Get user details
                users = connection.execute(text("SELECT user FROM mysql.user")).fetchall()

                # Get schemas for each user (in MySQL, schemas are synonymous with databases)
                schemas = connection.execute(text("SHOW DATABASES")).fetchall()

                # Get tables, columns, row counts, and their sizes for each schema
                tables_info = {}
                for schema in schemas:
                    schema_name = schema[0]
                    tables = connection.execute(text(f"""
                        SELECT table_name, 
                               COUNT(*) AS column_count, 
                               ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS table_size,
                               (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = '{schema_name}' AND table_name = t.table_name) AS column_count,
                               (SELECT COUNT(*) FROM {schema_name}.information_schema.tables WHERE table_name = t.table_name) AS row_count
                        FROM information_schema.tables t
                        WHERE table_schema = '{schema_name}'
                        GROUP BY t.table_name
                    """)).fetchall()
                    tables_info[schema_name] = {
                        table[0]: {"column_count": table[1], "size_in_mb": table[2], "row_count": table[3]} for
                        table in tables}

                # Add information to db_info
                db_info.update({
                    "db_name": db_name,
                    "db_version": db_version,
                    "db_size": f"{db_size} MB",
                    "uptime": str(uptime),
                    "users": [user[0] for user in users],
                    "schemas": [schema[0] for schema in schemas],
                    "tables_info": tables_info,
                    "server": connection.execute(text("SELECT @@hostname")).scalar(),
                    "port": connection.execute(text("SHOW VARIABLES LIKE 'port'")).fetchone()[1]
                })

            elif db_type == 'mssql':
                # SQL Server specific queries
                db_name = connection.execute(text("SELECT DB_NAME()")).scalar()
                db_version = connection.execute(text("SELECT @@version")).scalar()
                db_size = connection.execute(text("EXEC sp_spaceused")).fetchone()[0]  # Get database size info
                uptime = connection.execute(text("SELECT sqlserver_startup_time FROM sys.dm_os_sys_info")).scalar()

                # Get user details
                users = connection.execute(text("SELECT name FROM sys.sysusers")).fetchall()

                # Get schemas for each user (for SQL Server, schemas are available in information_schema)
                schemas = connection.execute(text("SELECT schema_name FROM information_schema.schemata")).fetchall()

                # Get tables, columns, row counts, and their sizes for each schema
                tables_info = {}
                for schema in schemas:
                    schema_name = schema[0]
                    tables = connection.execute(text(f"""
                        SELECT t.name AS table_name, 
                               c.column_count, 
                               p.rows AS row_count, 
                               SUM(a.total_pages) * 8 / 1024 AS size_in_mb
                        FROM {schema_name}.sys.tables t
                        INNER JOIN {schema_name}.sys.indexes i ON t.object_id = i.object_id
                        INNER JOIN {schema_name}.sys.partitions p ON i.object_id = p.object_id
                        INNER JOIN {schema_name}.sys.allocation_units a ON p.partition_id = a.container_id
                        CROSS APPLY (
                            SELECT COUNT(*) AS column_count
                            FROM {schema_name}.sys.columns c
                            WHERE c.object_id = t.object_id
                        ) c
                        GROUP BY t.name, p.rows
                    """)).fetchall()
                    tables_info[schema_name] = {
                        table[0]: {"column_count": table[1], "row_count": table[2], "size_in_mb": table[3]} for
                        table in tables}

                # Add information to db_info
                db_info.update({
                    "db_name": db_name,
                    "db_version": db_version,
                    "db_size": db_size,
                    "uptime": str(uptime),
                    "users": [user[0] for user in users],
                    "schemas": [schema[0] for schema in schemas],
                    "tables_info": tables_info,
                    "server": connection.execute(text("SELECT SERVERPROPERTY('MachineName')")).scalar(),
                    "port": connection.execute(text("SELECT SERVERPROPERTY('ProductVersion')")).scalar()
                })
            else:
                db_info = {}

        # Update the connection details with the database info
        connection_details.update(db_info)

        return models.ComponentStatus(status="ok", details=engine.pool.status()), connection_details
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        return models.ComponentStatus(status="error",
                                      details=str(e)), {}  # Return empty dict1 for connection details on error


async def check_redis_health(redis_client=None):
    redis_connection_details = {}
    if redis_client:  # Check if redis_client is initialized
        try:
            await redis_client.ping()  # Asynchronous ping if your redis client supports it
            redis_connection_stats = redis_client.connection_pool.connection_kwargs  # Example - adjust based on redis client library

            if redis_connection_stats:  # Check if stats are available
                redis_connection_details = {
                    "connection_kwargs": str(redis_connection_stats),  # Basic representation - enhance as needed
                    # Add more relevant Redis connection pool stats here if your client provides them
                }
            return models.ComponentStatus(status="ok"), redis_connection_details
        except Exception as e:
            logger.error(f"Redis health check failed: {e}", exc_info=True)
            return models.ComponentStatus(status="error", details=str(e)), {}
    else:
        return None, redis_connection_details  # Return empty dict if no redis client


async def get_application_stats():
    """Collects general application statistics."""
    global REQUEST_COUNT, ERROR_COUNT, RESPONSE_TIMES
    avg_response_time = sum(RESPONSE_TIMES) / len(RESPONSE_TIMES) if RESPONSE_TIMES else 0
    return {
        "uptime": get_uptime(),
        "request_count": REQUEST_COUNT,
        "error_count": ERROR_COUNT,
        "average_response_time_ms": f"{avg_response_time:.2f}",  # Format to 2 decimal places
    }


@router.get("/health", response_model=models.HealthCheckResponse)
async def health_check(db_session: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.

    Provides detailed health information about the application and its dependencies.
    Includes status of database, Redis (if configured), application version, uptime, timestamp,
    connection statistics, and general application statistics.
    Used by monitoring systems for in-depth health assessment.

    Returns:
        HealthCheckResponse: Detailed health status of the application.
    """
    db_status, db_conn_details = await check_database_health(db=db_session)
    redis_status, redis_conn_details = await check_redis_health()  # Will be None if redis_client is not configured
    app_stats = await get_application_stats()

    overall_status = "ok"
    if db_status.status != "ok" or (
            redis_status and redis_status and redis_status.status != "ok"):  # Check Redis status only if it's checked
        overall_status = "degraded"
        if db_status.status == "error":  # Database error makes it more critical
            overall_status = "critical"  # Or "error" - choose severity level

    connection_stats = {
        "database": db_conn_details,
        "redis": redis_conn_details,
        # Add other connection stats here if needed
    }

    return models.HealthCheckResponse(
        status=overall_status,
        # version=settings.APP_VERSION,
        uptime=get_uptime(),
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        redis=redis_status,  # Include Redis status even if None (for optional component)
        connections=connection_stats,
        application=app_stats,
        # Include other component statuses here
    )


async def get_user_statistics_data(db_session: Session):  # Extracted data fetching to separate function
    """Fetches and calculates user statistics data from the database."""
    # 1. Number of logged-in users (Active Sessions - depends on how you track sessions, this is a simplified example)
    logged_in_users_count = 0  # <--- Replace with actual active session count logic if available

    # 2. Total active users in the last hour (users who logged in or were active in last hour)
    active_users_last_hour_count = db_session.query(func.count(User.id)).filter(
        User.last_login_at >= datetime.now(timezone.utc) - timedelta(hours=1)
        # Assuming User model and last_login_at column
    ).scalar() or 0

    # 3. Inactive users in the last 30 days (users with no login/activity in last 30 days)
    inactive_users_30_days_count = db_session.query(func.count(User.id)).filter(
        User.last_login_at < datetime.now(timezone.utc) - timedelta(days=30)
        # Assuming User model and last_login_at column
    ).scalar() or 0

    # 4. Count of valid access tokens (This is complex and depends heavily on token storage and management)
    valid_access_tokens_count = 0  # <---  Complex to count directly in stateless JWT. May need to track refresh tokens or active sessions.

    # 5. Top 10 users with highest failed login attempts
    top_10_failed_login_users_query = db_session.query(User.email, User.failed_login_attempts).order_by(
        User.failed_login_attempts.desc()
    ).limit(10)
    top_10_failed_login_users_list = [{"email": user.email, "failed_attempts": user.failed_login_attempts} for user in
                                      top_10_failed_login_users_query]

    # 6. Total failed login attempts across all users
    total_failed_login_attempts = db_session.query(func.sum(User.failed_login_attempts)).scalar() or 0

    # 7. New users in the last 24 hours
    new_users_last_24_hours_count = db_session.query(func.count(User.id)).filter(
        User.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)  # Assuming User model and created_at column
    ).scalar() or 0

    # 8. User roles distribution
    user_roles_distribution_data = db_session.query(User.role, func.count(User.id)).group_by(User.role).all()
    user_roles_distribution_dict = {role: count for role, count in user_roles_distribution_data}

    # 9. Security events in last hour (Example: OTP requests - adjust based on your security event tracking)
    security_events_last_hour_count = db_session.query(func.count(OTP.id)).filter(
        # Assuming OTP model and relevant timestamp
        OTP.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)  # Adjust timestamp column and model as needed
    ).scalar() or 0  # Example - counting OTP requests as security events, enhance based on actual events

    # 10. Average Login Time (Placeholder - Needs instrumentation during login process)
    average_login_time_ms = 0.0  # <--- Placeholder - Implement login time tracking in auth service

    return {
        "logged_in_users": logged_in_users_count,
        "total_active_users_last_hour": active_users_last_hour_count,
        "inactive_users_last_30_days": inactive_users_30_days_count,
        "valid_access_tokens_count": valid_access_tokens_count,
        "top_10_failed_login_users": top_10_failed_login_users_list,
        "total_failed_login_attempts_all_users": total_failed_login_attempts,
        "new_users_last_24_hours": new_users_last_24_hours_count,
        "user_roles_distribution": user_roles_distribution_dict,
        "security_events_last_hour": security_events_last_hour_count,
        "average_login_time_ms": average_login_time_ms,
    }


@router.get("/user_stats", response_model=models.UserStatsResponse, dependencies=[Depends(verify_access_token)])
async def get_user_statistics(db_session: Session = Depends(get_db)):
    """
    Endpoint to retrieve comprehensive user statistics for monitoring and admin purposes.
    Requires a valid access token for authorization.

    Returns:
        UserStatsResponse: Detailed user statistics including active users, inactive users,
                         failed login attempts, new users, role distribution, and security events.

    Raises:
        HTTPException (401 Unauthorized): If the access token is invalid or missing.
        HTTPException (500 Internal Server Error): If there's an error fetching user statistics.
    """
    try:
        user_stats_data = await get_user_statistics_data(db_session)  # Call data fetching function
        return models.UserStatsResponse(**user_stats_data)  # Create and return response model

    except AuthenticationError as auth_e:
        logger.warning(f"Unauthorized access attempt to /user_stats: {auth_e.detail}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=auth_e.detail,
                            headers={"WWW-Authenticate": "Bearer"})
    except CustomException as custom_e:
        logger.warning(f"Error fetching user stats: {custom_e.detail}")
        raise HTTPException(status_code=custom_e.status_code, detail=custom_e.detail)
    except Exception as e:
        logger.error(f"Unexpected error fetching user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user statistics"
        )


@router.get("/protected", dependencies=[Depends(verify_access_token)])
async def protected_resource(user_email: str = Depends(verify_access_token)):
    """
    Example protected route.

    This endpoint requires a valid access token to be accessed.
    Upon successful verification of the access token, it returns a success message
    including the email of the user extracted from the token.

    Security:
        - Authentication: Uses JWT access token verification via `verify_access_token` dependency.
        - Authorization: Implicitly handled by token verification; only users with valid tokens can access.

    Returns:
        ProtectedResponse: A message confirming access and the user's email.

    Raises:
        HTTPException (401 Unauthorized): If the access token is invalid or missing.
    """
    try:
        return {"message": f"Protected resource accessed by user: {user_email}"}
    except AuthenticationError as e:  # Catch specific AuthenticationError from security utils
        logger.warning(f"Unauthorized access attempt to /protected: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=e.detail, headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:  # Catch unexpected errors
        logger.error(f"Unexpected error accessing /protected: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


# --- Request Counter Middleware (Example - Basic) ---
async def request_counter_middleware(request: Request, call_next):
    """Middleware to count requests and errors, and measure response times."""
    global REQUEST_COUNT, ERROR_COUNT, RESPONSE_TIMES
    REQUEST_COUNT += 1
    start_time = time.time()
    response = None  # Initialize response to None to handle exceptions properly
    try:
        response = await call_next(request)  # Process the request
    except Exception as e:
        ERROR_COUNT += 1
        raise e  # Re-raise exception after counting error
    finally:  # Ensure response time is recorded even if exception occurs
        process_time = time.time() - start_time
        RESPONSE_TIMES.append(process_time * 1000)  # Store response time in milliseconds
        if len(RESPONSE_TIMES) > 100:  # Keep only last 100 response times for moving average (adjust as needed)
            RESPONSE_TIMES.pop(0)  # Remove oldest response time

    return response


# --- Initialize FastAPI App and Include Middleware ---
app = FastAPI()  # Create FastAPI instance (if you haven't already)
app.include_router(router)  # Include the monitoring router

app.middleware("http")(request_counter_middleware)  # Add the middleware to the app


# --- Readiness Check Endpoint (Example - Extend as needed) ---
@app.get("/ready", tags=["System"])
async def readiness_check():
    """
    Readiness check endpoint to verify application readiness to serve requests.
    Extend this to check database connectivity, cache availability, etc.
    """
    try:
        with SessionLocal() as db:  # Check database connectivity
            db.execute("SELECT 1")  # Simple DB query
        return {"status": "ready"}
    except Exception as e:
        logger.warning(f"Readiness check failed: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not ready")
