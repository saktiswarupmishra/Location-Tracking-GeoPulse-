"""
LocationHistory document shape for the `location_history` collection.

Uses GeoJSON Point. Has a TTL index on `timestamp` for auto-expiry.

{
  _id,
  userId,

  location: {
    type: "Point",
    coordinates: [longitude, latitude]
  },

  accuracy,
  speed,
  heading,
  timestamp
}
"""

LOCATION_HISTORY_COLLECTION = "location_history"
