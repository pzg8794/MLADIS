# Metrics And Financial Inputs

Private checklist for building lender-grade financials, forecasts, and investor materials.

## Revenue Inputs

| Input | Source | Status | Notes |
| --- | --- | --- | --- |
| Airbnb gross booking revenue by month | Airbnb export / payout reports | Todo | Separate by listing where possible. |
| Airbnb payout net revenue by month | Airbnb payout reports / bank records | Todo | Include platform fees and adjustments. |
| Direct-booking revenue | MLADIS app / Stripe / PayPal | Todo | Future once direct bookings are live. |
| Cleaning fees collected | Airbnb/app/payment exports | Todo | Track separately from rent if possible. |
| Damage deposit holds/captures/releases | Stripe/PayPal/app records | Todo | Do not treat holds as revenue unless captured. |
| Extra bills / penalties / broken items | MLADIS invoices/payment records | Todo | Track by reason and property. |

## Booking And Operations Inputs

| Input | Source | Status | Notes |
| --- | --- | --- | --- |
| Reservation count by month | Airbnb/app database | Todo | Include cancelled vs completed. |
| Nights booked by month | Airbnb/app database | Todo | Needed for occupancy. |
| Available nights by listing | Calendar/app | Todo | Needed for occupancy denominator. |
| Average daily rate | Revenue / booked nights | Todo | Calculate by listing and channel. |
| Average stay length | Reservation history | Todo | Useful for marketing and cleaning costs. |
| Cancellation count/rate | Airbnb/app database | Todo | Separate owner/admin cancellations from guest cancellations. |
| Inquiry volume | Website agent/contact logs | Todo | Useful for conversion analysis. |
| Inquiry-to-booking conversion | App analytics | Todo | Useful for agent and UX ROI. |
| Review rating summary | Airbnb/public reviews/admin highlights | In progress | Use public-safe summaries. |

## Expense Inputs

| Input | Source | Status | Notes |
| --- | --- | --- | --- |
| Cleaning payments | Receipts/payment records | Todo | Split by listing/stay when possible. |
| Repairs and maintenance | Receipts/vendor records | Todo | Keep photos/receipts for larger repairs. |
| Supplies | Receipts/card records | Todo | Bedding, towels, toiletries, cleaning supplies. |
| Utilities/HOA/maintenance fees | Statements/receipts | Todo | Confirm foreign-property treatment with CPA. |
| Software/subscriptions | Card/bank records | Todo | Hosting, domains, API, email, SaaS tools. |
| Payment processor fees | Stripe/PayPal/export | Todo | Direct-booking cost of revenue. |
| Platform fees | Airbnb reports | Todo | Airbnb cost of revenue. |
| Marketing/ads | Ad platforms/receipts | Todo | Track campaign and channel. |
| Contractor payments/reimbursements | Transfer records/agreement | Todo | Tie to Diana contractor record and CPA review. |
| Legal/accounting/compliance | Invoices/receipts | Todo | LLC, publication, CPA, attorney, insurance. |

## Forecast Inputs

| Assumption | Draft value | Needs owner approval |
| --- | --- | --- |
| Target occupancy | TBD | Yes |
| Average nightly rate by listing | TBD | Yes |
| Direct-booking share target | TBD | Yes |
| Marketing budget | TBD | Yes |
| Cleaning cost per stay | TBD | Yes |
| Maintenance reserve | TBD | Yes |
| Software/API monthly budget | TBD | Yes |
| Refund/cancellation reserve | TBD | Yes |
| Damage reserve / claims assumption | TBD | Yes |
| Loan payment capacity | TBD | Yes |

## Outputs To Build

- Monthly revenue table.
- Monthly expense table.
- Monthly profit/loss.
- Cash-flow forecast.
- Direct-booking contribution margin.
- Booking funnel report.
- Use-of-funds model.
- Lender one-page summary.
- Investor metrics page.
