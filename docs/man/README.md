# dialtor Man Pages

This directory contains manual pages for dialtor in standard Unix man page format.

## Available Man Pages

- `dialtor.1` - Main dialtor command reference

## Installation

### Automatic Installation (via Makefile)

From the project root:

```bash
sudo make install-man
```

This will install the man page to `/usr/local/share/man/man1/dialtor.1`.

### Manual Installation

**System-wide (requires sudo):**

```bash
sudo cp dialtor.1 /usr/local/share/man/man1/
sudo mandb  # Update man database
```

**User-local (no sudo required):**

```bash
mkdir -p ~/.local/share/man/man1
cp dialtor.1 ~/.local/share/man/man1/
mandb  # Update man database
```

Make sure `~/.local/share/man` is in your `MANPATH`:

```bash
export MANPATH="$HOME/.local/share/man:$MANPATH"
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Usage

After installation, view the man page with:

```bash
man dialtor
```

Or view directly without installation:

```bash
man ./dialtor.1
```

## Verification

Check if the man page is installed correctly:

```bash
man -w dialtor
```

This should output the path to the installed man page.

## Uninstallation

**System-wide:**

```bash
sudo rm /usr/local/share/man/man1/dialtor.1
sudo mandb
```

**User-local:**

```bash
rm ~/.local/share/man/man1/dialtor.1
mandb
```
