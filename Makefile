# dialtor Makefile
# Installation targets for man pages and other assets

PREFIX ?= /usr/local
MANDIR = $(PREFIX)/share/man
MAN1DIR = $(MANDIR)/man1

.PHONY: help install-man uninstall-man

help:
	@echo "dialtor Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install-man     Install man pages (requires sudo)"
	@echo "  uninstall-man   Remove installed man pages (requires sudo)"
	@echo "  help            Show this help message"

install-man:
	@echo "Installing man pages to $(MAN1DIR)..."
	@mkdir -p $(MAN1DIR)
	@install -m 644 docs/man/dialtor.1 $(MAN1DIR)/dialtor.1
	@if command -v mandb >/dev/null 2>&1; then \
		echo "Updating man database..."; \
		mandb -q; \
	fi
	@echo "Man pages installed successfully!"
	@echo "View with: man dialtor"

uninstall-man:
	@echo "Removing man pages from $(MAN1DIR)..."
	@rm -f $(MAN1DIR)/dialtor.1
	@if command -v mandb >/dev/null 2>&1; then \
		echo "Updating man database..."; \
		mandb -q; \
	fi
	@echo "Man pages uninstalled successfully!"
