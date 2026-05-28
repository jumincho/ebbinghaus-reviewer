// HYPOTHETICAL RECONSTRUCTION — not the original.
// Event handler names (listclicked / btnclick) come from ToDoListView.g.cs's
// switch on connection ids 1 (PageListBox MouseDoubleClick) + 3 (Button Click).
// The Add-button click in particular delegates to the ViewModel command so
// AddItemCommand's CanExecute (non-empty DraftTitle) governs the button.

using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Review_Reminder.MVVM.Model;
using Review_Reminder.MVVM.ViewModel;

namespace Review_Reminder.MVVM.View
{
    public partial class ToDoListView : UserControl
    {
        public ToDoListView()
        {
            InitializeComponent();
        }

        // Connection id 1: PageListBox.MouseDoubleClick.
        private void listclicked(object sender, MouseButtonEventArgs e)
        {
            if (PageListBox.SelectedItem is ReviewItem item)
            {
                // The original probably opened a detail view; here we just
                // show the next-review time so the wiring stays demonstrable.
                MessageBox.Show(
                    $"Next review: {item.NextReviewTime:yyyy-MM-dd HH:mm}",
                    item.Title);
            }
        }

        // Connection id 3: Add button Click. Routes through the VM command so
        // CanExecute (non-empty title) still applies.
        private void btnclick(object sender, RoutedEventArgs e)
        {
            if (DataContext is ToDoListViewModel vm && vm.AddItemCommand.CanExecute(null))
            {
                vm.AddItemCommand.Execute(null);
            }
        }
    }
}
