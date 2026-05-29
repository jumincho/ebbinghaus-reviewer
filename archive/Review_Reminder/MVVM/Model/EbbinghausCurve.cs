using System;
using System.Collections.Generic;

namespace Review_Reminder.MVVM.Model
{
    /// <summary>
    /// Pure-function source of truth for the spaced-repetition offsets.
    /// All time arithmetic in the rest of the app passes through here so
    /// that "change the curve" is a one-file edit.
    /// </summary>
    public static class EbbinghausCurve
    {
        /// <summary>
        /// The four textbook offsets at which the app surfaces a reminder.
        ///
        /// Slot 0 = 10 minutes — a "did it stick" check.
        /// Slot 1 = 1 day      — first full-sleep consolidation.
        /// Slot 2 = 1 week     — medium-term reinforcement.
        /// Slot 3 = 1 month    — long-term reinforcement.
        /// </summary>
        public static readonly IReadOnlyList<TimeSpan> DefaultOffsets = new[]
        {
            TimeSpan.FromMinutes(10),
            TimeSpan.FromDays(1),
            TimeSpan.FromDays(7),
            TimeSpan.FromDays(30),
        };

        /// <summary>
        /// Given a study time, returns the absolute review timestamps for
        /// each slot of the curve. Pure function: feed it the same input
        /// and you get the same output, no DateTime.Now anywhere.
        /// </summary>
        public static IReadOnlyList<DateTime> OffsetsFrom(DateTime studiedAt)
        {
            var result = new DateTime[DefaultOffsets.Count];
            for (var i = 0; i < DefaultOffsets.Count; i++)
            {
                result[i] = studiedAt + DefaultOffsets[i];
            }
            return result;
        }

        /// <summary>
        /// Short human label for a given slot — used by TodolistReminder
        /// when populating the four TextBlocks.
        /// </summary>
        public static string LabelForSlot(int slot)
        {
            switch (slot)
            {
                case 0: return "10 min";
                case 1: return "1 day";
                case 2: return "1 week";
                case 3: return "1 month";
                default: throw new ArgumentOutOfRangeException(nameof(slot));
            }
        }
    }
}
