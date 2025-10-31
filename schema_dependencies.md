# Core DocType Dependency Map

## Counterparty

**Link Fields**

- `company` → `Company`

**Child Tables**

None

## Project

**Link Fields**

- `company` → `Company`
- `customer` → `Counterparty`

**Child Tables**

None

## Contract

**Link Fields**

- `company` → `Company`
- `customer` → `Counterparty`
- `project` → `Project`

**Child Tables**

None

## Contract Stage

**Link Fields**

- `contract` → `Contract`

**Child Tables**

None

## Service Act

**Link Fields**

- `contract` → `Contract`
- `stage` → `Contract Stage`

**Child Tables**

None

## Service Request

**Link Fields**

- `assigned_to` → `User`
- `company` → `Company`
- `customer` → `Customer`
- `linked_report` → `Service Report`
- `project` → `Service Project`
- `service_department` → `Service Department`
- `service_object` → `Service Object`

**Child Tables**

- `attachments` (child table `Document Attachment Item`)
- `financial_details` (child table `Financial Detail`)
- `photos` (child table `Request Photo Attachment Item`)

## Service Report

**Link Fields**

- `company` → `Company`
- `service_department` → `Service Department`
- `service_request` → `Service Request`

**Child Tables**

- `documents` (child table `Service Report Document Item`)
- `work_items` (child table `Service Report Work Item`)

## Invoice

**Link Fields**

- `company` → `Company`
- `project` → `Service Project`
- `sales_invoice` → `Sales Invoice`

**Child Tables**

- `attachments` (child table `Document Attachment Item`)

## Invoice Item

**Link Fields**

- `invoice` → `Invoice`

**Child Tables**

None

## Payment

**Link Fields**

- `article` → `Cashflow Article`
- `company` → `Company`
- `counterparty` → `Counterparty`

**Child Tables**

None

## Payment Allocation

**Link Fields**

- `invoice` → `Invoice`
- `payment` → `Payment`

**Child Tables**

None

## Cashflow Article

**Link Fields**

None

**Child Tables**

None

## Data Issue

**Link Fields**

None

**Child Tables**

None

## Stg Raw

**Link Fields**

None

**Child Tables**

None

## Document

**Link Fields**

- `company` → `Company`
- `counterparty` → `Counterparty`
- `employee` → `User`

**Child Tables**

None

## Service Maintenance Schedule

**Link Fields**

- `company` → `Company`
- `customer` → `Customer`
- `service_project` → `Service Project`

**Child Tables**

- `items` (child table `Service Maintenance Schedule Item`)

## Service Object

**Link Fields**

- `company` → `Company`
- `customer` → `Customer`
- `default_engineer` → `User`
- `project` → `Service Project`

**Child Tables**

None

## Service Project

**Link Fields**

- `company` → `Company`
- `customer` → `Customer`
- `default_engineer` → `User`
- `project_manager` → `User`
- `service_department` → `Service Department`

**Child Tables**

- `attachments` (child table `Document Attachment Item`)
- `objects` (child table `Project Object Item`)
- `telegram_users` (child table `Project Telegram User Item`)
