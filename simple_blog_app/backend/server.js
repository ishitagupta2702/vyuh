

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
require('dotenv').config();

//routes import
const usersRoute = require('./routes/users');
const postsRoute = require('./routes/posts');

//Express App
const app = express();
app.use(cors());
app.use(express.json());

//route setup
app.use('/api/users', usersRoute);
app.use('/api/posts', postsRoute);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', message: 'Blog API is running!' });
});

//DB Config - Use local MongoDB or mock data
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/simple_blog';

mongoose.connect(MONGODB_URI, { 
  useNewUrlParser: true, 
  useUnifiedTopology: true 
})
.then(() => {
  console.log('✅ MongoDB database connection established successfully!');
})
.catch((error) => {
  console.log('❌ MongoDB connection failed:', error.message);
  console.log('📝 Running in mock mode - no database connection');
});

//Server startup
const port = process.env.PORT || 5000;
app.listen(port, () => {
    console.log(`🚀 Server is running on port: ${port}`);
    console.log(`📡 Health check: http://localhost:${port}/api/health`);
    console.log(`👥 Users API: http://localhost:${port}/api/users`);
    console.log(`📝 Posts API: http://localhost:${port}/api/posts`);
});

