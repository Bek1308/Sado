/// Something Sado wants to do on the user's computer. It only runs after the
/// user says yes.
final class PendingAction {
  const PendingAction({required this.id, required this.description});

  final String id;
  final String description;
}
