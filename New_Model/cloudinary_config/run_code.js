app.post('/run-model', requireRole('recruiter'), async (req, res) => {
  const company = req.session.user.company

  // Call a Python script or API here with the company name
  const { exec } = require('child_process')

  exec(`python3 new_main.py ${company}`, (err, stdout, stderr) => {
    if (err) return res.status(500).send(stderr)
    res.send(`<pre>${stdout}</pre>`)
  })
})
