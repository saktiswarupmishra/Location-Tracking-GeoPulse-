"""
User document shape for the `users` collection.

{
  _id,
  phone,
  name,
  profileImage,
  email,
  isOnline,
  lastActive,
  privacySettings: {
    discoverability: "everyone" | "contacts" | "nobody",
    locationSharingEnabled: true | false
  },
  emergencyContacts: [userId, ...],
  blockedUsers: [userId, ...],
  createdAt,
  updatedAt
}
"""

USER_COLLECTION = "users"
