using System.Windows.Input;

namespace Review_Reminder.MVVM.ViewModel
{
    /// <summary>
    /// Owns the five "page" ViewModels and the currently-shown one. Holding
    /// instances (rather than newing per click) preserves state across nav.
    /// </summary>
    public class MainViewModel : BaseViewModel
    {
        private object _currentView;

        public HomeViewModel HomeVM { get; }
        public ToDoListViewModel ToDoListVM { get; }
        public CalendarViewModel CalendarVM { get; }
        public ReviewSystemViewModel ReviewSystemVM { get; }
        public InformationViewModel InformationVM { get; }

        public object CurrentView
        {
            get => _currentView;
            private set => SetField(ref _currentView, value);
        }

        public ICommand ShowHomeCommand { get; }
        public ICommand ShowToDoListCommand { get; }
        public ICommand ShowCalendarCommand { get; }
        public ICommand ShowReviewSystemCommand { get; }
        public ICommand ShowInformationCommand { get; }

        public MainViewModel()
        {
            // The scheduler is wired into App.xaml.cs's OnStartup; pull
            // the live instance from the App singleton.
            var scheduler = App.Scheduler;

            HomeVM = new HomeViewModel();
            ToDoListVM = new ToDoListViewModel(scheduler);
            CalendarVM = new CalendarViewModel(scheduler);
            ReviewSystemVM = new ReviewSystemViewModel(scheduler);
            InformationVM = new InformationViewModel();

            ShowHomeCommand = new RelayCommand(() => CurrentView = HomeVM);
            ShowToDoListCommand = new RelayCommand(() => CurrentView = ToDoListVM);
            ShowCalendarCommand = new RelayCommand(() => CurrentView = CalendarVM);
            ShowReviewSystemCommand = new RelayCommand(() => CurrentView = ReviewSystemVM);
            ShowInformationCommand = new RelayCommand(() => CurrentView = InformationVM);

            CurrentView = HomeVM;
        }
    }
}
