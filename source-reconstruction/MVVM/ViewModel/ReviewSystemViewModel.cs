// HYPOTHETICAL RECONSTRUCTION — not the original.
// Filters the registered ReviewItems down to "items with a slot due today"
// and exposes them as a flat list for ReviewSystemView's DataGrid.

using System;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows.Input;
using Review_Reminder.MVVM.Model;
using Review_Reminder.Services;

namespace Review_Reminder.MVVM.ViewModel
{
    public class ReviewSystemViewModel : BaseViewModel
    {
        private readonly IReviewScheduler _scheduler;

        public ObservableCollection<TodayEntry> TodaysReviews { get; }
            = new ObservableCollection<TodayEntry>();

        public ICommand RefreshCommand { get; }
        public ICommand AcknowledgeCommand { get; }

        public ReviewSystemViewModel(IReviewScheduler scheduler)
        {
            _scheduler = scheduler;
            RefreshCommand = new RelayCommand(_ => Refresh());
            AcknowledgeCommand = new RelayCommand(p => Acknowledge(p as TodayEntry));

            if (_scheduler != null)
            {
                _scheduler.ItemScheduled += (_, __) => Refresh();
                _scheduler.ReminderFired += (_, __) => Refresh();
                Refresh();
            }
        }

        private void Refresh()
        {
            TodaysReviews.Clear();
            var today = DateTime.Today;
            foreach (var item in _scheduler.Items)
            {
                var schedule = new ReviewSchedule(item);
                foreach (var when in schedule.ReviewsOn(today))
                {
                    TodaysReviews.Add(new TodayEntry
                    {
                        Item = item,
                        DueAt = when,
                    });
                }
            }
        }

        private void Acknowledge(TodayEntry entry)
        {
            if (entry == null) return;
            entry.Item.NextSlotIndex = Math.Min(
                entry.Item.NextSlotIndex + 1,
                entry.Item.ReviewTimes?.Count ?? 0);
            Refresh();
        }
    }

    public class TodayEntry
    {
        public ReviewItem Item { get; set; }
        public DateTime DueAt { get; set; }
        public string Title => Item?.Title;
    }
}
