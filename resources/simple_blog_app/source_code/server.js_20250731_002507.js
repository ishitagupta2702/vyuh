

const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');

//routes import
const usersRoute = require('./routes/users');
const postsRoute = require('./routes/posts');

//Express App
const app = express();
app.use(cors());
app.use(express.json());

//route setup
app.use('/users', usersRoute);
app.use('/posts', postsRoute);

//DB Config
const uri = process.env.ATLAS_URI;
mongoose.connect(uri, { useNewUrlParser: true, useCreateIndex: true, useUnifiedTopology: true });
const connection = mongoose.connection;
connection.once('open', () => {
  console.log('MongoDB database connection established successfully!');
});

//Server startup
const port = process.env.PORT || 5000;
app.listen(port, () => {
    console.log(`Server is running on port: ${port}`);
});

