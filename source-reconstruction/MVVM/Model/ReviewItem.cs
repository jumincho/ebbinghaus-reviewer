// HYPOTHETICAL RECONSTRUCTION — not the original.
// A single study item the user has logged. Notes is optional; Title is the
// short label that appears in the ToDoList and the TodolistReminder popup
// (the BAML field `todoname` in TodolistReminder.g.cs binds to this).

using System;
using System.Collections.Generic;

namespace Review_Reminder.MVVM.Model
{
    /// <summary>
    /// One unit of "stuff to remember". The lifecycle is intentionally simple:
    ///   1. user enters Title (+ optional Notes) via ToDoListView
    ///   2. StudiedAt is stamped to DateTime.Now
    ///   3. ReviewScheduler caches the offsets from EbbinghausCurve and
    ///      queues a notification for each one
    /// </summary>
    public class ReviewItem
    {
        public Guid Id { get; set; } = Guid.NewGuid();

        /// <summary>Short label shown in the list and reminder popup.</summary>
        public string Title { get; set; }

        /// <summary>Free-form notes — body text of the reminder.</summary>
        public string Notes { get; set; }

        /// <summary>When the user first studied the item. Anchor of the curve.</summary>
        public DateTime StudiedAt { get; set; }

        /// <summary>
        /// Cached review timestamps. Populated by ReviewScheduler.Schedule
        /// from EbbinghausCurve.OffsetsFrom(StudiedAt).
        /// </summary>
        public IReadOnlyList<DateTime> ReviewTimes { get; set; }

        /// <summary>
        /// Which slot of the curve the user is currently waiting on. Bumped
        /// each time a reminder fires + is acknowledged.
        /// </summary>
        public int NextSlotIndex { get; set; }

        public DateTime? NextReviewTime =>
            ReviewTimes != null && NextSlotIndex < ReviewTimes.Count
                ? ReviewTimes[NextSlotIndex]
                : (DateTime?)null;

        public bool IsCompleted =>
            ReviewTimes != null && NextSlotIndex >= ReviewTimes.Count;
    }
}
