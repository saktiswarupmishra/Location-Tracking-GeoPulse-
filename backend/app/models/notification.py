"""
Notification document shape for the `notifications` collection.

{
  _id,
  userId,

  type,           // LOCATION_REQUEST | REQUEST_ACCEPTED | ...
  title,
  message,

  data: {},       // arbitrary payload

  isRead,
  createdAt
}
"""

NOTIFICATIONS_COLLECTION = "notifications"
