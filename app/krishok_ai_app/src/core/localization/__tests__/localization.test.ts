import i18n from '../i18n';

describe('Bangla and English localization', () => {
  it('has translated initial screen labels in both languages', async () => {
    await i18n.changeLanguage('en');
    expect(i18n.t('nav.home')).toBe('Home');
    expect(i18n.t('scanner.unavailableTitle')).toBe('Detection is not ready yet');
    await i18n.changeLanguage('bn');
    expect(i18n.t('nav.home')).toBe('হোম');
    expect(i18n.t('scanner.unavailableTitle')).toBe('শনাক্তকরণ এখনো প্রস্তুত নয়');
  });
});
