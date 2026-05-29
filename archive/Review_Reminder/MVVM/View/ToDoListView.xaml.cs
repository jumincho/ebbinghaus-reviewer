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

        // PageListBox.MouseDoubleClick.
        private void listclicked(object sender, MouseButtonEventArgs e)
        {
            if (PageListBox.SelectedItem is ReviewItem item)
            {
                MessageBox.Show(
                    $"Next review: {item.NextReviewTime:yyyy-MM-dd HH:mm}",
                    item.Title);
            }
        }

        // Add button Click. Routes through the VM command so CanExecute
        // (non-empty title) still applies.
        private void btnclick(object sender, RoutedEventArgs e)
        {
            if (DataContext is ToDoListViewModel vm && vm.AddItemCommand.CanExecute(null))
            {
                vm.AddItemCommand.Execute(null);
            }
        }
    }
}
