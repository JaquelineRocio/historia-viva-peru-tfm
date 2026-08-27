import { canonicalYoutubeUrl, extractYoutubeId } from './youtube-id.util';

describe('YouTube URL validation', () => {
  it.each([
    ['https://www.youtube.com/watch?v=gZpo1PjY0ao', 'gZpo1PjY0ao'],
    ['https://youtu.be/gZpo1PjY0ao?t=10', 'gZpo1PjY0ao'],
    ['https://www.youtube.com/shorts/gZpo1PjY0ao', 'gZpo1PjY0ao'],
    ['gZpo1PjY0ao', 'gZpo1PjY0ao'],
  ])('accepts %s', (value, expected) => {
    expect(extractYoutubeId(value)).toBe(expected);
  });

  it.each([
    'http://www.youtube.com/watch?v=gZpo1PjY0ao',
    'https://evil.example/watch?v=gZpo1PjY0ao',
    'https://youtube.com.evil.example/watch?v=gZpo1PjY0ao',
    'https://www.youtube.com/watch?v=short',
    'javascript:alert(1)',
  ])('rejects %s', (value) => {
    expect(extractYoutubeId(value)).toBeNull();
    expect(canonicalYoutubeUrl(value)).toBeNull();
  });

  it('removes tracking parameters from the stored URL', () => {
    expect(canonicalYoutubeUrl('https://youtu.be/gZpo1PjY0ao?si=tracking')).toBe(
      'https://www.youtube.com/watch?v=gZpo1PjY0ao',
    );
  });
});
