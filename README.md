# RecallAgent

**An AI customer retention agent for local service businesses.**

## Overview

RecallAgent is a portfolio project focused on helping local service businesses bring customers back at the right time.

Many small businesses provide services that customers may need again later, such as car washing, auto detailing, home deep cleaning, carpet cleaning, lawn care, pest control, or similar recurring services. The challenge is that business owners often do not have a reliable system for tracking when each customer should be contacted again.

RecallAgent is designed to solve that problem by analyzing customer service history and creating timely follow-up reminders. Instead of relying on manual notes or fixed calendar reminders, the system uses customer records, service types, and past service dates to decide when a follow-up message should be prepared.

## Problem Statement

Local service businesses often lose repeat revenue because customer follow-up is inconsistent.

A customer may complete a service today and need the same or related service again in one month, three months, or six months. But as the number of customers grows, it becomes difficult for the business owner to remember:

- Which customers are due for a reminder
- What service each customer received
- When the last service happened
- How often that service is usually repeated
- Whether the customer has already been contacted
- What message should be sent

Without an organized follow-up process, businesses may miss opportunities to re-engage satisfied customers and encourage repeat bookings.

## Project Goal

The goal of RecallAgent is to create a simple, understandable, and production-inspired AI agent system that helps businesses manage customer retention.

The system will store customer and service history, review that data on a schedule, decide whether a customer should receive a reminder, generate a personalized follow-up message, and place that reminder into a queue for review or delivery.

## Example Use Case

A customer visits a car wash business and receives an interior cleaning service. Based on the service type and date, RecallAgent may determine that the customer should be reminded again after several weeks.

For a home deep cleaning service, the reminder timing may be much longer. The system should understand that different services have different follow-up patterns.

## Planned Agent Workflow

RecallAgent will use a lightweight multi-agent workflow:

- **Service Insight Agent**: Reviews the customer's service history and service type.
- **Reminder Decision Agent**: Decides whether a reminder should be created.
- **Message Writer Agent**: Creates a personalized follow-up message.
- **Reminder Scheduler Agent**: Adds the reminder to a queue for review or delivery.

## Portfolio Focus

This project is intended to demonstrate:

- Practical AI agent design
- Data-driven decision making
- Customer retention automation
- Clear system reasoning and decision logs
- A simple workflow that can be explained and expanded over time

The first version will focus on clarity, correctness, and a strong end-to-end demo before adding advanced features.
