# `command -v freecadcmd` covers a PATH-configured install; the explicit
# fallback covers a fresh macOS Homebrew-cask install, whose bin/ isn't on
# PATH by default (see install-freecad's own printed hint).
FREECAD ?= $(shell command -v freecadcmd 2>/dev/null || echo /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd)
FREECAD_GUI ?= $(shell command -v freecad 2>/dev/null || echo /Applications/FreeCAD.app/Contents/Resources/bin/freecad)
DESIGNS := $(patsubst designs/%/generate.py,%,$(wildcard designs/*/generate.py))
OPEN_TARGETS := $(addprefix open-,$(DESIGNS))

.PHONY: all list clean install-freecad $(DESIGNS) $(OPEN_TARGETS)

all: $(DESIGNS)

list:
	@echo $(DESIGNS)

install-freecad:
	@uname_s=$$(uname -s 2>/dev/null || echo unknown); \
	case "$$uname_s" in \
		Darwin) \
			echo "Installing FreeCAD via Homebrew..."; \
			brew install --cask freecad; \
			echo "If 'freecadcmd' isn't on PATH, add:"; \
			echo '  export PATH="/Applications/FreeCAD.app/Contents/Resources/bin:$$PATH"' ;; \
		Linux) \
			if command -v apt-get >/dev/null 2>&1; then \
				echo "Installing FreeCAD via apt..."; \
				if sudo apt-get update && sudo apt-get install -y freecad; then \
					: ; \
				elif command -v snap >/dev/null 2>&1; then \
					echo "apt has no 'freecad' candidate on this release (dropped from Ubuntu 24.04/noble onward) - falling back to snap..."; \
					sudo snap install freecad; \
					printf '#!/bin/sh\nexec /snap/bin/freecad.cmd -- "$$@"\n' | sudo tee /usr/local/bin/freecadcmd >/dev/null; \
					sudo chmod +x /usr/local/bin/freecadcmd; \
					printf '#!/bin/sh\nexec /snap/bin/freecad -- "$$@"\n' | sudo tee /usr/local/bin/freecad >/dev/null; \
					sudo chmod +x /usr/local/bin/freecad; \
					echo "Wrapped (not symlinked) - 'snap run' intercepts leading flags like -c itself"; \
					echo "unless separated with --, so a plain symlink to freecad.cmd would break every build."; \
				else \
					echo "apt has no 'freecad' candidate and snap isn't available either."; \
					echo "Install FreeCAD manually: https://www.freecad.org/downloads.php"; \
					exit 1; \
				fi ;; \
			elif command -v dnf >/dev/null 2>&1; then \
				echo "Installing FreeCAD via dnf..."; \
				sudo dnf install -y freecad; \
			elif command -v pacman >/dev/null 2>&1; then \
				echo "Installing FreeCAD via pacman..."; \
				sudo pacman -S --noconfirm freecad; \
			else \
				echo "No known package manager (apt/dnf/pacman) found."; \
				echo "Install FreeCAD manually: https://www.freecad.org/downloads.php"; \
				exit 1; \
			fi ;; \
		*) \
			echo "Unrecognized OS ($$uname_s)."; \
			echo "On Windows, install FreeCAD inside WSL2 (Ubuntu) and run 'make install-freecad' there."; \
			echo "Without WSL2, install FreeCAD manually: https://www.freecad.org/downloads.php"; \
			exit 1 ;; \
	esac
	@echo "Installing Python build deps (trimesh, matplotlib) into system python3..."
	@python3 -m pip install -r requirements.txt || python3 -m pip install --break-system-packages -r requirements.txt
	@fc_py="/Applications/FreeCAD.app/Contents/Resources/bin/python"; \
	if [ -x "$$fc_py" ]; then \
		echo "Installing Python build deps into FreeCAD's own bundled python (needed for GLB export inside generate.py)..."; \
		"$$fc_py" -m pip install -r requirements.txt; \
	fi

# freecadcmd only auto-executes .FCMacro/.FCStd files positionally, never plain
# .py (confirmed against FreeCAD 1.1.1) - so generate.py must be run via runpy
# from -c, not passed as a bare positional argument.
$(DESIGNS):
	$(eval OUTDIR := $(if $(OUT),$(OUT),designs/$@/outputs))
	@mkdir -p $(OUTDIR)
	@if ! command -v "$(FREECAD)" >/dev/null 2>&1; then \
		echo "FreeCAD not found ('$(FREECAD)'). Run 'make install-freecad', or set FREECAD=/path/to/freecadcmd."; \
		exit 1; \
	fi
	$(FREECAD) -c "import runpy, sys; sys.argv = ['generate.py', '--outdir', '$(OUTDIR)']; runpy.run_path('designs/$@/generate.py', run_name='__main__')"
	@stl=$$(ls $(OUTDIR)/*.stl 2>/dev/null | head -n1); \
	if [ -n "$$stl" ]; then \
		python3 scripts/render_preview.py "$$stl" "$(OUTDIR)/preview.png" || \
			echo "warning: preview.png render failed (missing matplotlib/trimesh in system python3? run 'make install-freecad') - the real outputs above are still fine"; \
	fi

clean:
	@for d in $(DESIGNS); do rm -rf designs/$$d/outputs; done

# `make open-<name>` builds the design (if needed) then opens the most
# useful FreeCAD-readable output in the FreeCAD GUI: an assembly/preview
# .FCStd if the design has one (richer - multiple objects, full parts
# tree), else the plain .step. Tries $(FREECAD_GUI) on PATH first, then
# falls back to macOS's `open -a FreeCAD`, then the Homebrew cask's known
# binary path.
$(OPEN_TARGETS): open-%: %
	@out_dir=designs/$*/outputs; \
	file=$$(ls $$out_dir/*.FCStd 2>/dev/null | head -n1); \
	if [ -z "$$file" ]; then file=$$(ls $$out_dir/*.step 2>/dev/null | head -n1); fi; \
	if [ -z "$$file" ]; then \
		echo "No FreeCAD-openable output found in $$out_dir"; exit 1; \
	fi; \
	echo "Opening $$file in FreeCAD..."; \
	if command -v "$(FREECAD_GUI)" >/dev/null 2>&1; then \
		"$(FREECAD_GUI)" "$$file" & \
	elif [ "$$(uname -s)" = "Darwin" ] && [ -d "/Applications/FreeCAD.app" ]; then \
		open -a FreeCAD "$$file"; \
	elif [ -x "/Applications/FreeCAD.app/Contents/Resources/bin/freecad" ]; then \
		"/Applications/FreeCAD.app/Contents/Resources/bin/freecad" "$$file" & \
	else \
		echo "FreeCAD GUI not found ('$(FREECAD_GUI)' not on PATH, no /Applications/FreeCAD.app)."; \
		echo "Run 'make install-freecad' first, or open $$file manually."; \
		exit 1; \
	fi
