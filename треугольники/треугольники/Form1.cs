using static System.Console;
namespace треугольники
{
    public partial class Form1 : Form
    {
        public Form1()
        {
            InitializeComponent();



        }

        private void button1_Click(object sender, EventArgs e)
        {
            label2.Text = string.Empty;
            bool flagA = double.TryParse(textBox1.Text, out double a);
            if (!flagA)
            {
                MessageBox.Show("Вы не ввели число");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;

            }
            bool flagB = double.TryParse(textBox2.Text, out double b);
            if (!flagB)
            {
                MessageBox.Show("Вы не ввели число");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;

            }
            bool flagC = double.TryParse(textBox3.Text, out double c);
            if (!flagC)
            {
                MessageBox.Show("Вы не ввели число");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;

            }
            if (a <= 0 || c <= 0 || b <= 0)
            {
                MessageBox.Show("Вы указали сторону, которая меньше либо равна 0!");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;
            }


            if (a + b <= c || a + c <= b || b + c <= a)
            {
                MessageBox.Show("Одна сторона больше суммы двух других или равна ей!");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;
            }
            if (a > 1000000 || b > 1000000 || c > 1000000)
            {
                MessageBox.Show("Вы указали слишком большое число!");
                textBox1.Text = string.Empty;
                textBox2.Text = string.Empty;
                textBox3.Text = string.Empty;
                return;
            }


            if (a == b & b == c)
            {
                label2.Text = "Это равносторонний треугольник";
                return;

            }
            if (a == b || b == c || a == c)
            {
                label2.Text = "Это равнобедренный треугольник";
                return;

            }
            if (a != b & b != c)
            {
                label2.Text = "Это разносторонний треугольник";
                return;
            }

        }
    }
}