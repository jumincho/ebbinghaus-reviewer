// HYPOTHETICAL RECONSTRUCTION — not the original.
// Drives ToDoListView. Inferred fields from ToDoListView.g.cs:
//   - PageListBox  (ListBox)
//   - inputtextbox (TextBox)
//   - listclicked  (MouseDoubleClick handler on PageListBox)
//   - btnclick     (Click handler on an add Button)

using System;
using System.Collections.ObjectModel;
using System.Windows.Input;
using Review_Reminder.MVVM.Model;
using Review_Reminder.Services;

namespace Review_Reminder.MVVM.ViewModel
{
    /// <summary>
    /// Owns the list of registered study items and dispatches new ones into
    /// the scheduler. Lives on the dispatcher thread; the scheduler is what
    /// takes care of timer wiring.
    /// </summary>
    public class ToDoListViewModel : BaseViewModel
    {
        private readonly IReviewScheduler _scheduler;
        private string _draftTitle;
        private ReviewItem _selectedItem;

        public ObservableCollection<ReviewItem> Items { get; } = new ObservableCollection<ReviewItem>();

        /// <summary>
        /// The text typed into the inputtextbox before clicking the add button.
        /// </summary>
        public string DraftTitle
        {
            get => _draftTitle;
            set => SetField(ref _draftTitle, value);
        }

        public ReviewItem SelectedItem
        {
            get => _selectedItem;
            set => SetField(ref _selectedItem, value);
        }

        public ICommand AddItemCommand { get; }
        public ICommand RemoveItemCommand { get; }

        public ToDoListViewModel(IReviewScheduler scheduler)
        {
            _scheduler = scheduler ?? throw new ArgumentNullException(nameof(scheduler));

            AddItemCommand = new RelayCommand(
                _ => AddItem(),
                _ => !string.IsNullOrWhiteSpace(DraftTitle));

            RemoveItemCommand = new RelayCommand(
                _ => RemoveSelected(),
                _ => SelectedItem != null);
        }

        private void AddItem()
        {
            var item = new ReviewItem
            {
                Title = DraftTitle.Trim(),
                Notes = string.Empty,
                StudiedAt = DateTime.Now,
            };

            // Scheduler stamps ReviewTimes onto the item and queues the
            // four future reminders. After this the model is a complete
            // record that other VMs can read.
            _scheduler.Schedule(item);

            Items.Add(item);
            DraftTitle = string.Empty;
        }

        private void RemoveSelected()
        {
            if (SelectedItem == null) return;
            _scheduler.Cancel(SelectedItem);
            Items.Remove(SelectedItem);
            SelectedItem = null;
        }
    }
}
