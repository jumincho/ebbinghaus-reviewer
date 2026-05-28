// HYPOTHETICAL RECONSTRUCTION — not the original.
// Read-only projection over a ReviewItem's schedule. Pure model code;
// no Notification or Dispatcher dependencies here.

using System;
using System.Collections.Generic;
using System.Linq;

namespace Review_Reminder.MVVM.Model
{
    /// <summary>
    /// Read-only view of a single item's review schedule.
    /// CalendarViewModel maps a list of ReviewSchedules onto Syncfusion
    /// SfScheduler appointments; ReviewSystemViewModel filters today's.
    /// </summary>
    public class ReviewSchedule
    {
        public ReviewSchedule(ReviewItem item)
        {
            if (item == null) throw new ArgumentNullException(nameof(item));
            Item = item;
        }

        public ReviewItem Item { get; }

        public string Title => Item.Title;

        public DateTime StudiedAt => Item.StudiedAt;

        public IReadOnlyList<DateTime> AllReviewTimes => Item.ReviewTimes ?? new DateTime[0];

        public DateTime? NextReviewTime => Item.NextReviewTime;

        /// <summary>
        /// Are *any* of this item's review timestamps inside the local day
        /// of <paramref name="date"/>? Used by ReviewSystemViewModel.
        /// </summary>
        public bool HasReviewOn(DateTime date)
        {
            var dayStart = date.Date;
            var dayEnd = dayStart.AddDays(1);
            return AllReviewTimes.Any(t => t >= dayStart && t < dayEnd);
        }

        /// <summary>
        /// Materialise just the review timestamps that fall on <paramref name="date"/>.
        /// </summary>
        public IEnumerable<DateTime> ReviewsOn(DateTime date)
        {
            var dayStart = date.Date;
            var dayEnd = dayStart.AddDays(1);
            return AllReviewTimes.Where(t => t >= dayStart && t < dayEnd);
        }
    }
}
