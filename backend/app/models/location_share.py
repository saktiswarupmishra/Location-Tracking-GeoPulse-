"""
LocationShare document shape for the `location_shares` collection.

{
  _id,
  ownerId,          // the user who owns the location (sharer)
  viewerId,         // the user who can view the location

  status,           // pending | accepted | rejected | revoked | expired

  permissions: {
    liveLocation:      true | false,
    locationHistory:   true | false
  },

  startedAt,
  expiresAt,        // null = until stopped
  stoppedAt,

  createdAt,
  updatedAt
}
"""

LOCATION_SHARES_COLLECTION = "location_shares"
