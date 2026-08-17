// cypress/e2e/dashboard.cy.ts
// Task 93: E2E Tests using Cypress

describe('Tozalash Servis Admin Dashboard E2E', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5173')
  })

  it('shows the Dashboard page by default', () => {
    cy.contains('Umumiy Hisobotlar').should('be.visible')
  })

  it('navigates to Map page', () => {
    cy.contains('Xarita').click()
    cy.contains('Xarita & Jonli Kuzatuv').should('be.visible')
  })

  it('navigates to Chat page', () => {
    cy.contains('Chat').click()
    cy.contains('Jonli Chat').should('be.visible')
  })

  it('can send a message in chat', () => {
    cy.contains('Chat').click()
    cy.get('input[placeholder="Xabar yozing..."]').type('Salom, bu test xabari')
    cy.get('button').last().click()
    cy.contains('Salom, bu test xabari').should('be.visible')
  })

  it('navigates to Calendar page', () => {
    cy.contains('Taqvim').click()
    cy.contains('Taqvim va Rejalar').should('be.visible')
  })

  it('toggles dark/light theme', () => {
    cy.contains("Mavzuni o'zgartirish").click()
    cy.get('html').should('have.class', 'light')
    cy.contains("Mavzuni o'zgartirish").click()
    cy.get('html').should('have.class', 'dark')
  })
})
