using System.Windows;
using Review_Reminder.MVVM.Model;
using Review_Reminder.MVVM.View;

namespace Review_Reminder.Services
{
    /// <summary>
    /// Default INotificationService implementation: spin a TodolistReminder
    /// inside a top-level Window and show it.
    /// </summary>
    public class NotificationService : INotificationService
    {
        public void Show(ReviewItem item, int slot)
        {
            if (item == null) return;

            // Pop on the dispatcher thread so we don't break WPF affinity.
            Application.Current?.Dispatcher.Invoke(() =>
            {
                var content = new TodolistReminder();
                content.Bind(item, slot);

                var window = new Window
                {
                    Title = "Review Reminder",
                    Width = 360,
                    Height = 240,
                    WindowStartupLocation = WindowStartupLocation.Manual,
                    Topmost = true,
                    Content = content,
                };

                // Position bottom-right of the working area (toast-y).
                var workArea = SystemParameters.WorkArea;
                window.Left = workArea.Right - window.Width - 16;
                window.Top = workArea.Bottom - window.Height - 16;

                window.Show();
            });
        }
    }
}
