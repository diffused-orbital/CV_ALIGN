const session = require('express-session')
const bcrypt = require('bcrypt')

app.use(session({
  secret: 'GhNtyL1tRnTOWchvUSlJqsFUExU',
  resave: false,
  saveUninitialized: true
}))

app.use(express.urlencoded({ extended: true }))
const PORT = 3000
app.listen(PORT, () => console.log(`Server running on port ${PORT}`))

// LOGIN
app.post('/login', async (req, res) => {
  const { username, password } = req.body
  const user = users.find(u => u.username === username)

  if (!user) return res.send('User not found')

  const match = await bcrypt.compare(password, user.password)
  if (!match) return res.send('Incorrect password')

  // Save user session
  req.session.user = {
    username: user.username,
    role: user.role,
    company: user.company
  }

  res.redirect('/dashboard')  // or separate page for each role
})

// LOGOUT
app.get('/logout', (req, res) => {
  req.session.destroy(err => {
    if (err) return res.send('Logout error')
    res.redirect('/')
  })
})
