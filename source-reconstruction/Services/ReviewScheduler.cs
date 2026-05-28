// HYPOTHETICAL RECONSTRUCTION — not the original.
// In-memory timer-based scheduler. The original was probably backed by
// DispatcherTimer (so callbacks ran on the UI thread); we use the same
// here. No persistence — the 2021 build had nothing in obj-Release that
// would suggest a database, and the FileListAbsolute.txt lists no
// settings/db files.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows.Threading;
using Review_Reminder.MVVM.Model;

namespace Review_Reminder.Services
{
    public class ReviewScheduler : IReviewScheduler
    {
        private readonly INotificationService _notifications;
        private readonly ObservableCollection<ReviewItem> _items = new ObservableCollection<ReviewItem>();
        private readonly Dictionary<Guid, List<DispatcherTimer>> _timers = new Dictionary<Guid, List<DispatcherTimer>>();
        private bool _disposed;

        public IReadOnlyCollection<ReviewItem> Items => _items;

        public event EventHandler<ReviewItem> ItemScheduled;
        public event EventHandler<ReviewItem> ItemCancelled;
        public event EventHandler<ReminderFiredEventArgs> ReminderFired;

        public ReviewScheduler(INotificationService notifications)
        {
            _notifications = notifications ?? throw new ArgumentNullException(nameof(notifications));
        }

        public void Schedule(ReviewItem item)
        {
            if (item == null) throw new ArgumentNullException(nameof(item));

            item.ReviewTimes = EbbinghausCurve.OffsetsFrom(item.StudiedAt);
            _items.Add(item);

            var perItem = new List<DispatcherTimer>();
            for (var slot = 0; slot < item.ReviewTimes.Count; slot++)
            {
                var when = item.ReviewTimes[slot];
                var delay = when - DateTime.Now;
                if (delay <= TimeSpan.Zero) continue;

                var slotCopy = slot;       // capture for closure
                var timer = new DispatcherTimer { Interval = delay };
                timer.Tick += (_, __) =>
                {
                    timer.Stop();
                    Fire(item, slotCopy);
                };
                timer.Start();
                perItem.Add(timer);
            }
            _timers[item.Id] = perItem;

            ItemScheduled?.Invoke(this, item);
        }

        public void Cancel(ReviewItem item)
        {
            if (item == null) return;
            if (_timers.TryGetValue(item.Id, out var timers))
            {
                foreach (var t in timers) t.Stop();
                _timers.Remove(item.Id);
            }
            _items.Remove(item);
            ItemCancelled?.Invoke(this, item);
        }

        private void Fire(ReviewItem item, int slot)
        {
            ReminderFired?.Invoke(this, new ReminderFiredEventArgs(item, slot));
            _notifications.Show(item, slot);
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;
            foreach (var t in _timers.Values.SelectMany(x => x)) t.Stop();
            _timers.Clear();
        }
    }
}
