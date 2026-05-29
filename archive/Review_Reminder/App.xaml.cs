using System.Windows;
using Review_Reminder.Services;

namespace Review_Reminder
{
    /// <summary>
    /// Application entry point.
    ///
    /// Loads the Theme/MenuButtonTheme resource dictionary via App.xaml,
    /// wires up cross-cutting services (review scheduler + notifications),
    /// and lets WPF dispatch to MainWindow per StartupUri.
    /// </summary>
    public partial class App : Application
    {
        /// <summary>
        /// Singleton-style service registry. Kept deliberately tiny — the
        /// project predates any DI container, so services are passed by hand.
        /// </summary>
        public static IReviewScheduler Scheduler { get; private set; }
        public static INotificationService Notifications { get; private set; }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Order matters: the notification service is what the scheduler
            // calls into when a due time fires, so build it first.
            Notifications = new NotificationService();
            Scheduler = new ReviewScheduler(Notifications);
        }

        protected override void OnExit(ExitEventArgs e)
        {
            Scheduler?.Dispose();
            base.OnExit(e);
        }
    }
}
