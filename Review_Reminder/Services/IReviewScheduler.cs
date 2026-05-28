using System;
using System.Collections.Generic;
using Review_Reminder.MVVM.Model;

namespace Review_Reminder.Services
{
    /// <summary>EventArgs payload for ReminderFired.</summary>
    public class ReminderFiredEventArgs : EventArgs
    {
        public ReviewItem Item { get; }
        public int Slot { get; }

        public ReminderFiredEventArgs(ReviewItem item, int slot)
        {
            Item = item;
            Slot = slot;
        }
    }

    /// <summary>
    /// Service abstraction that ToDoListViewModel / CalendarViewModel /
    /// ReviewSystemViewModel all depend on. The interface seam keeps the
    /// VMs unit-testable without dragging in DispatcherTimer.
    /// </summary>
    public interface IReviewScheduler : IDisposable
    {
        /// <summary>All items currently tracked by the scheduler.</summary>
        IReadOnlyCollection<ReviewItem> Items { get; }

        /// <summary>Raised after Schedule(item) finishes wiring an item.</summary>
        event EventHandler<ReviewItem> ItemScheduled;

        /// <summary>Raised after Cancel(item) drops an item.</summary>
        event EventHandler<ReviewItem> ItemCancelled;

        /// <summary>
        /// Raised when a reminder for an item actually fires (the
        /// NotificationService is what then opens TodolistReminder).
        /// </summary>
        event EventHandler<ReminderFiredEventArgs> ReminderFired;

        /// <summary>
        /// Compute review timestamps from item.StudiedAt via EbbinghausCurve,
        /// attach them to the item, then queue a timer for each future slot.
        /// </summary>
        void Schedule(ReviewItem item);

        /// <summary>Stop all pending timers for <paramref name="item"/> and forget it.</summary>
        void Cancel(ReviewItem item);
    }
}
