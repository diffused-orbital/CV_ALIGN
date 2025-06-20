const users = [
  {
    username: 'recruiter1',
    password: bcrypt.hashSync('recruiterpass', 10), // hashed password
    role: 'recruiter',
    company: 'CompanyA'
  },
  {
    username: 'candidate1',
    password: bcrypt.hashSync('candidatepass', 10),
    role: 'candidate',
    company: 'CompanyA'
  }
]
