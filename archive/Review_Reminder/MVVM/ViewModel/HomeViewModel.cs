namespace Review_Reminder.MVVM.ViewModel
{
    public class HomeViewModel : BaseViewModel
    {
        private string _greeting = "Welcome back!";
        public string Greeting
        {
            get => _greeting;
            set => SetField(ref _greeting, value);
        }

        public string Tagline =>
            "Spaced repetition along the Ebbinghaus forgetting curve.";
    }
}
