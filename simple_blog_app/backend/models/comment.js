

const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const CommentSchema = new Schema({
  content: {type: String, required: true},
  postId: {type: Schema.Types.ObjectId, ref: 'Post'},
  author: {type: Schema.Types.ObjectId, ref: 'User'},
  createdAt: {type: Date, default: Date.now}
});

module.exports = mongoose.model('Comment', CommentSchema);

