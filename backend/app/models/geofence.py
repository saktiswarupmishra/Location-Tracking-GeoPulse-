"""
Geofence document shape for the `geofences` collection.

{
  _id,
  userId,

  name,            // "Home", "Office", etc.

  center: {
    type: "Point",
    coordinates: [longitude, latitude]
  },

  radiusMeters,
  isActive,

  createdAt,
  updatedAt
}
"""

GEOFENCES_COLLECTION = "geofences"
