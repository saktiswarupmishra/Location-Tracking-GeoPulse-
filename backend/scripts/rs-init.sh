#!/bin/bash
# MongoDB Replica Set Initializer Script
echo "Initializing replica set rs0..."
mongosh --eval "
try {
  rs.status();
} catch (e) {
  rs.initiate({
    _id: 'rs0',
    members: [{ _id: 0, host: 'mongodb-primary:27017' }]
  });
}
"
