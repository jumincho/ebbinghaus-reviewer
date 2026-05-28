// HYPOTHETICAL RECONSTRUCTION — not the original MainWindow.xaml.cs.
// The handler names below (Close_Click + Mimimize_Click — sic, original typo)
// are taken from build-artifacts/obj-Release/MainWindow.g.cs's switch on
// connection ids 1 and 2.

using System.Windows;
using System.Windows.Input;

namespace Review_Reminder
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Borderless window drag — clicked-and-held on the title bar.
        /// </summary>
        protected override void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            base.OnMouseLeftButtonDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        // Connection id 1 in MainWindow.g.cs.
        private void Close_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        // Connection id 2 in MainWindow.g.cs. The method name keeps the
        // original spelling (Mimimize vs. Minimize) on purpose — that
        // typo is what the compiled BAML actually references.
        private void Mimimize_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }
    }
}
