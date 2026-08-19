"""
LiveLocation document shape for the `live_locations` collection.

Uses GeoJSON Point — coordinates are [longitude, latitude].

{
  userId,

  location: {
    type: "Point",
    coordinates: [longitude, latitude]
  },

  accuracy,
  speed,
  heading,

  timestamp,
  updatedAt
}
"""

LIVE_LOCATIONS_COLLECTION = "live_locations"
