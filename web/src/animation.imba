export def animate t, styles 
	if t.hasFlag(styles.className)
		# Already applied
		return false

	let names = ['animationend', 'webkitanimationend']

	let remover = do
		t.unflag(styles.className)
		t.dom.removeEventListener(name, remover) for name in names

	t.dom.addEventListener(name, remover, false) for name in names

	setTimeout(remover, 500)

	t.flag(styles.className)

	return true
