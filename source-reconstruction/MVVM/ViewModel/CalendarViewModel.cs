// HYPOTHETICAL RECONSTRUCTION — not the original.
// CalendarView.g.cs declares a field `CVM` of type
// Review_Reminder.MVVM.ViewModel.CalendarViewModel — i.e. the View instantiates
// its own VM through XAML. So the VM has a default ctor and lazily binds to
// the live scheduler via App.Scheduler. We also expose Appointments for the
// Syncfusion SfScheduler (`Schedule` field, also from CalendarView.g.cs).

using System.Collections.ObjectModel;
using System.Linq;
using Review_Reminder.MVVM.Model;
using Review_Reminder.Services;

namespace Review_Reminder.MVVM.ViewModel
{
    /// <summary>
    /// Maps every review timestamp on every item into a Syncfusion SfScheduler
    /// appointment object. We re-materialise on every Refresh — the per-item
    /// schedule list is tiny (4 entries each), so a full rebuild is cheaper
    /// than maintaining a diff.
    /// </summary>
    public class CalendarViewModel : BaseViewModel
    {
        private readonly IReviewScheduler _scheduler;

        public ObservableCollection<CalendarAppointment> Appointments { get; }
            = new ObservableCollection<CalendarAppointment>();

        public CalendarViewModel()
            : this(App.Scheduler)
        {
        }

        public CalendarViewModel(IReviewScheduler scheduler)
        {
            _scheduler = scheduler;
            if (_scheduler != null)
            {
                _scheduler.ItemScheduled += (_, __) => Refresh();
                _scheduler.ItemCancelled += (_, __) => Refresh();
                Refresh();
            }
        }

        private void Refresh()
        {
            Appointments.Clear();
            foreach (var item in _scheduler.Items)
            {
                if (item.ReviewTimes == null) continue;
                foreach (var (when, slot) in item.ReviewTimes.Select((t, i) => (t, i)))
                {
                    Appointments.Add(new CalendarAppointment
                    {
                        Subject = item.Title,
                        Notes = item.Notes,
                        StartTime = when,
                        EndTime = when.AddMinutes(15),
                        Slot = slot,
                    });
                }
            }
        }
    }

    /// <summary>
    /// Shape consumed by SfScheduler bindings (subject/start/end). Exposing
    /// Slot lets the calendar colour-code the four Ebbinghaus stages.
    /// </summary>
    public class CalendarAppointment
    {
        public string Subject { get; set; }
        public string Notes { get; set; }
        public System.DateTime StartTime { get; set; }
        public System.DateTime EndTime { get; set; }
        public int Slot { get; set; }
    }
}
