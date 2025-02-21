package database

// import (
// 	"adwise-service/model"

// 	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
// )

// // Neo4jDB represents a Neo4j database connection.
// type Neo4jDB struct {
// 	driver neo4j.Driver
// }

// // NewNeo4jDB creates a new Neo4j database connection.
// func NewNeo4jDB(uri, username, password string) (*Neo4jDB, error) {
// 	driver, err := neo4j.NewDriver(uri, neo4j.BasicAuth(username, password, ""))
// 	if err != nil {
// 		return nil, err
// 	}

// 	// Verify the connection
// 	// ctx := context.Background()
// 	if err := driver.VerifyConnectivity(); err != nil {
// 		return nil, err
// 	}

// 	return &Neo4jDB{driver: driver}, nil
// }

// // Close closes the Neo4j database connection.
// func (n *Neo4jDB) Close() error {
// 	return n.driver.Close()
// }

// // CreateUser creates a new user in the graph database.
// func (n *Neo4jDB) CreateUser(user *model.User) error {
// 	// ctx := context.Background()
// 	session := n.driver.NewSession(neo4j.SessionConfig{})
// 	defer session.Close()

// 	_, err := session.Run(`
// 		CREATE (u:User {id: $id, email: $email, name: $name})
// 	`, map[string]interface{}{
// 		"id":    user.ID,
// 		"email": user.Email,
// 		"name":  user.Name,
// 	})
// 	return err
// }

// // AddFriend creates a friendship relationship between two users.
// func (n *Neo4jDB) AddFriend(userID1, userID2 uint) error {
// 	// ctx := context.Background()
// 	session := n.driver.NewSession(neo4j.SessionConfig{})
// 	defer session.Close()

// 	_, err := session.Run(`
// 		MATCH (u1:User {id: $userID1}), (u2:User {id: $userID2})
// 		CREATE (u1)-[:FRIEND]->(u2)
// 	`, map[string]interface{}{
// 		"userID1": userID1,
// 		"userID2": userID2,
// 	})
// 	return err
// }

// // GetFriends retrieves the friends of a user.
// func (n *Neo4jDB) GetFriends(userID uint) ([]model.User, error) {
// 	// ctx := context.Background()
// 	session := n.driver.NewSession(neo4j.SessionConfig{})
// 	defer session.Close()

// 	result, err := session.Run(`
// 		MATCH (u:User {id: $userID})-[:FRIEND]->(friend:User)
// 		RETURN friend.id AS id, friend.email AS email, friend.name AS name
// 	`, map[string]interface{}{
// 		"userID": userID,
// 	})
// 	if err != nil {
// 		return nil, err
// 	}

// 	var friends []model.User
// 	for result.Next() {
// 		record := result.Record()
// 		friends = append(friends, model.User{
// 			ID:    record.Values[0].(uint),
// 			Email: record.Values[1].(string),
// 			Name:  record.Values[2].(string),
// 		})
// 	}

// 	return friends, nil
// }
