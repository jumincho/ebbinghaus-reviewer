// HYPOTHETICAL RECONSTRUCTION — not the original.
// Trivial VM — the Information page is read-only educational text about
// the Ebbinghaus curve. The VM just centralises the copy so it can
// localise later (Korean ↔ English) without view-side edits.

using System.Collections.Generic;

namespace Review_Reminder.MVVM.ViewModel
{
    public class InformationViewModel : BaseViewModel
    {
        public string Title => "About the Ebbinghaus curve";

        public string Intro =>
            "Hermann Ebbinghaus (1850–1909) was a German psychologist who pioneered the " +
            "experimental study of memory. His forgetting-curve research showed that " +
            "memorised material is lost rapidly unless deliberately reviewed.";

        public string HowItWorks =>
            "This app schedules four reviews per study item, spaced along the curve. " +
            "Acknowledging each reminder advances the item to the next slot.";

        public IReadOnlyList<string> Schedule => new[]
        {
            "10 minutes after studying",
            "1 day after studying",
            "1 week after studying",
            "1 month after studying",
        };
    }
}
