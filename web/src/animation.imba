export def animate t, styles
	if t.hasFlag(styles.className)
		# Already applied
		return false

	let remover = do
		t.unflag(styles.className)
		t.dom.removeEventListener("animationend", remover)

	t.dom.addEventListener("animationend", remover, false)
	t.flag(styles.className)

	return true
