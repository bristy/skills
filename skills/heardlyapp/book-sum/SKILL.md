# book-sum

Generate extended summaries of books with full content and key ideas.

## What it does

- Return complete book summaries (no truncation)
- Extract 3 key ideas with full narratives
- Create actionable takeaways
- Format as readable text summary
- Provide comprehensive overview

## Installation

```bash
clawhub install book-sum
```

## Usage

```javascript
const BookSumSkill = require('book-sum');
const skill = new BookSumSkill();

const result = skill.generateTextSummary({
  title: 'Atomic Habits',
  author: 'James Clear',
  summary: 'Small changes compound into big results...'
});
```

## Output

Extended summary with:
- Full book summary
- 3 Key Ideas (complete content)
- Actionable takeaways
- Comprehensive overview

## License

MIT
