import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sado/features/account/domain/account.dart';

/// Google sign-in through Firebase, on Android.
final class FirebaseAccountService implements AccountService {
  FirebaseAccountService({required this.serverClientId});

  /// The project's web client id; Google signs the sign-in token for it.
  final String serverClientId;

  Future<void>? _ready;

  FirebaseAuth get _auth => FirebaseAuth.instance;

  Future<void> _prepare() => _ready ??= GoogleSignIn.instance.initialize(
    serverClientId: serverClientId,
  );

  @override
  bool get supported => true;

  @override
  Stream<Account?> get changes => _auth.authStateChanges().map(_account);

  @override
  Account? get current => _account(_auth.currentUser);

  @override
  Future<Account?> signIn() async {
    await _prepare();
    try {
      final google = await GoogleSignIn.instance.authenticate();
      final credential = GoogleAuthProvider.credential(
        idToken: google.authentication.idToken,
      );
      final signedIn = await _auth.signInWithCredential(credential);
      return _account(signedIn.user);
    } on GoogleSignInException catch (error) {
      if (error.code == GoogleSignInExceptionCode.canceled) return null;
      rethrow;
    }
  }

  @override
  Future<void> signOut() async {
    await _prepare();
    await GoogleSignIn.instance.signOut();
    await _auth.signOut();
  }

  @override
  Future<String?> idToken() async => _auth.currentUser?.getIdToken();

  static Account? _account(User? user) => user == null
      ? null
      : Account(
          name: user.displayName ?? user.email ?? '',
          email: user.email ?? '',
          photoUrl: user.photoURL,
        );
}

/// The computer app, which never signs in.
final class NoAccountService implements AccountService {
  const NoAccountService();

  @override
  bool get supported => false;

  @override
  Stream<Account?> get changes => const Stream.empty();

  @override
  Account? get current => null;

  @override
  Future<Account?> signIn() async => null;

  @override
  Future<void> signOut() async {}

  @override
  Future<String?> idToken() async => null;
}
