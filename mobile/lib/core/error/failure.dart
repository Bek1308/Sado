sealed class Failure implements Exception {
  const Failure(this.message);

  final String message;
}

final class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

final class ServerFailure extends Failure {
  const ServerFailure(super.message);
}
