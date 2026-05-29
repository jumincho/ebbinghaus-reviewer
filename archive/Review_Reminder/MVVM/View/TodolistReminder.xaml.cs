using System.Windows.Controls;
using System.Windows.Media;
using Review_Reminder.MVVM.Model;

namespace Review_Reminder.MVVM.View
{
    public partial class TodolistReminder : UserControl
    {
        private static readonly Brush ActiveBrush = Brushes.White;
        private static readonly Brush InactiveBrush = (Brush)new BrushConverter().ConvertFromString("#888");

        public TodolistReminder()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Populate the popup. <paramref name="slot"/> is the curve index
        /// (0..3) corresponding to which reminder is firing; the matching
        /// TextBlock is highlighted, the others stay dim.
        /// </summary>
        public void Bind(ReviewItem item, int slot)
        {
            if (item == null) return;

            todoname.Text = item.Title;

            var blocks = new[] { first, snd, thd, forth };
            for (var i = 0; i < blocks.Length; i++)
            {
                blocks[i].Text = EbbinghausCurve.LabelForSlot(i);
                blocks[i].Foreground = i == slot ? ActiveBrush : InactiveBrush;
                blocks[i].FontWeight = i == slot
                    ? System.Windows.FontWeights.Bold
                    : System.Windows.FontWeights.Normal;
            }
        }
    }
}
