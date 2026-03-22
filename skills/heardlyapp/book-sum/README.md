# book-sum

Generate extended summaries of books with full content and key ideas.

## Installation

```bash
clawhub install book-sum
```

## Usage

```javascript
const BookSumSkill = require('book-sum');
const skill = new BookSumSkill();

// Generate extended text summary
const result = skill.generateTextSummary({
  title: 'Atomic Habits',
  author: 'James Clear',
  summary: 'Small changes compound into big results...'
});
```

## Features

- Extended text summaries (no truncation)
- 3 key ideas with full narratives
- Actionable takeaways
- Comprehensive book overview
- Complete content preservation

## Output Format

- Book metadata
- Full original summary
- 3 key ideas with complete takeaways
- Comprehensive overview

## License

MIT
