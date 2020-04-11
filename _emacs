; =============================================================
;
; Stephen's Emacs Configuration File
; <stephen.gould@anu.edu.au>
;
; =============================================================

; font size
(set-face-attribute 'default nil :height 120)

; window size
(if (window-system)
    (set-frame-height (selected-frame) 100))
(if (window-system)
    (set-frame-width (selected-frame) 100))

; turn off line fills
;(setq-default auto-fill-function 'do-auto-fill)
;(setq-default fill-column 74)
(setq-default truncate-lines t)

; set basic offset to 4 spaces
(setq c-basic-offset 4)
(setq tab-width 4 indent-tabs-mode nil)
(setq-default indent-tabs-mode nil)

; syntax highlighting
(global-font-lock-mode 1)

; cc-mode parametersization
(require 'cc-mode)
;(c-set-style 'c-lineup-arglist . nil)
(c-set-offset 'arglist-cont-nonempty '+)

(put 'upcase-region 'disabled nil)

; compilation
(global-set-key [(f9)] 'compile)
(setq compilation-window-height 8)

(setq compilation-finish-function
      (lambda (buf str)
        (if (string-match "exited abnormally" str)
            ;;there were errors
            (message "compilation errors, press C-x ` to visit")
          ;;no errors, make the compilation window go away in 0.5 seconds
          (run-at-time 0.5 nil 'delete-windows-on buf)
          (message "compilation successful"))))

(put 'erase-buffer 'disabled nil)

; matlab
(autoload 'matlab-mode "/home/sgould/share/matlab.el" "Enter Matlab mode." t)
(setq auto-mode-alist (cons '("\\.m\\'" . matlab-mode) auto-mode-alist))
(autoload 'matlab-shell "/home/sgould/share/matlab.el" "Interactive Matlab mode." t)

(custom-set-variables
  ;; custom-set-variables was added by Custom.
  ;; If you edit it by hand, you could mess it up, so be careful.
  ;; Your init file should contain only one such instance.
  ;; If there is more than one, they won't work right.
 '(inhibit-startup-screen t))
(custom-set-faces
  ;; custom-set-faces was added by Custom.
  ;; If you edit it by hand, you could mess it up, so be careful.
  ;; Your init file should contain only one such instance.
  ;; If there is more than one, they won't work right.
 )
