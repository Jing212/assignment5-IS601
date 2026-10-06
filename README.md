# Advanced Modular Python Calculator (IS 601)

---

## 🌟 Key Features & Design Patterns

This application incorporates key SOLID principles and software design patterns to achieve high modularity, testability, and maintainability:

1. **Facade Pattern (`app/calculator_repl.py`)**: Provides a unified, high-level interface (`CalculatorFacade`) that encapsulates subsystems like history management, memento caretakers, and configuration.
2. **Strategy Pattern (`app/operations.py`)**: Encapsulates arithmetic algorithms (`AddOperation`, `SubtractOperation`, `DivideOperation`, `PowerOperation`, `RootOperation`) behind an interchangeable `OperationStrategy` interface.
3. **Factory Pattern (`app/operations.py`)**: Uses `OperationFactory` to dynamically instantiate operation classes based on user string input.
4. **Memento Pattern (`app/calculator_memento.py`)**: Implements `CalculatorMemento` and `MementoCaretaker` with dual-stack mechanisms to enable seamless **Undo** and **Redo** capabilities.
5. **Observer Pattern (`app/history.py`)**: Features an `AutoSaveObserver` listening to calculation events on `HistoryManager` to trigger auto-saving or logging automatically.
6. **Data Persistence (`pandas`)**: Utilizes pandas DataFrames for structured storage, export, and reloading of calculation logs to/from CSV files.
7. **Error Handling & Paradigms**: Demonstrates both **LBYL** (Look Before You Leap) and **EAFP** (Easier to Ask Forgiveness than Permission) validation approaches (`app/input_validators.py`).

---

# 🛠️ Project Setup & Environment Configuration

### 🧩 1. Install Homebrew (Mac Only)
> Skip this step if you're on Windows.

Homebrew is a package manager for macOS used to easily install developer tools.

```bash
/bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"
brew --version
```
---

# 🧩 2. Install and Configure Git

## Install Git

- **MacOS (using Homebrew)**

```bash
brew install git
```

- **Windows**

Download and install [Git for Windows](https://git-scm.com/download/win).  
Accept the default options during installation.

**Verify Git:**

```bash
git --version
```

---

## Configure Git Globals

Set your name and email so Git tracks your commits properly:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

Confirm the settings:

```bash
git config --list
```

---

## Generate SSH Keys and Connect to GitHub

> Only do this once per machine.

1. Generate a new SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

(Press Enter at all prompts.)

2. Start the SSH agent:

```bash
eval "$(ssh-agent -s)"
```

3. Add the SSH private key to the agent:

```bash
ssh-add ~/.ssh/id_ed25519
```

4. Copy your SSH public key:

- **Mac/Linux:**

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

- **Windows (Git Bash):**

```bash
cat ~/.ssh/id_ed25519.pub | clip
```

5. Add the key to your GitHub account:
   - Go to [GitHub SSH Settings](https://github.com/settings/keys)
   - Click **New SSH Key**, paste the key, save.

6. Test the connection:

```bash
ssh -T git@github.com
```

You should see a success message.

---

# 🧩 3. Clone the Repository

Now you can safely clone the course project:

```bash
git clone <repository-url>
cd <repository-directory>
```

---

# 🛠️ 4. Install Python 3.10+

## Install Python

- **MacOS (Homebrew)**

```bash
brew install python
```

- **Windows**

Download and install [Python for Windows](https://www.python.org/downloads/).  
✅ Make sure you **check the box** `Add Python to PATH` during setup.

**Verify Python:**

```bash
python3 --version
```
or
```bash
python --version
```

---

## Create and Activate a Virtual Environment

(Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate.bat  # Windows
```

### Install Required Packages

```bash
pip install -r requirements.txt
```