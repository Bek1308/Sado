/// The Google account someone signed in to Sado with.
final class Account {
  const Account({required this.name, required this.email, this.photoUrl});

  final String name;
  final String email;
  final String? photoUrl;
}

/// Signing in with Google, so Sado keeps a memory of its own for each person
/// and knows the owner's phone from anyone else's.
abstract interface class AccountService {
  /// Whether this device can sign in at all; the computer app does not need
  /// to, it is the owner's by being on the owner's computer.
  bool get supported;

  Stream<Account?> get changes;

  Account? get current;

  /// Signs in, or returns `null` when the user closed Google's sheet.
  Future<Account?> signIn();

  Future<void> signOut();

  /// A fresh proof of who is signed in, for the server; `null` when nobody is.
  Future<String?> idToken();
}
