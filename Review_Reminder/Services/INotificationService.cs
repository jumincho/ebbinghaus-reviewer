using Review_Reminder.MVVM.Model;

namespace Review_Reminder.Services
{
    /// <summary>
    /// Thin abstraction over "open a TodolistReminder window for this
    /// item/slot". The seam exists so tests can stub the popup.
    /// </summary>
    public interface INotificationService
    {
        /// <summary>
        /// Pop a TodolistReminder for the given slot of the given item.
        /// The popup highlights one of `first` / `snd` / `thd` / `forth`
        /// according to which slot fired.
        /// </summary>
        void Show(ReviewItem item, int slot);
    }
}
